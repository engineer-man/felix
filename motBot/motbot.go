package main

import (
	ext "../discordgoExtension"
	"crypto/sha256"
	"fmt"
	"github.com/bwmarrin/discordgo"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"
)

var staffID string

type loginStruct struct {
	ID       string
	nickname string
	password string
	passTime int64
	channel  *discordgo.Channel
}

var users = make(map[string]loginStruct)
var messages = make(map[string][]string)

func main() {
	port := os.Args[1]
	http.HandleFunc("/", serveIndex)
	discord, err := discordgo.New("Bot notARealToken")
	errCheck("error creating discord session", err)
	errCheck("error retrieving account", err)
	discord.AddHandler(messageCreate)
	discord.AddHandler(func(discord *discordgo.Session, ready *discordgo.Ready) {
		err = discord.UpdateStatus(0, "reading your messages")
		if err != nil {
			fmt.Println("Error attempting to set my status")
		}
		servers := discord.State.Guilds
		fmt.Printf("motbot has started on %d servers\r\n", len(servers))
	})
	go checkPasswordTime(discord)
	discord.State.TrackRoles = true
	err = discord.Open()
	errCheck("Error opening connection to Discord", err)
	defer discord.Close()
	http.ListenAndServe(":"+port, nil)
}

func errCheck(msg string, err error) {
	if err != nil {
		fmt.Printf("%s: %+v", msg, err)
		panic(err)
	}
}

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {

	// Ignore all messages created by the bot itself
	// This isn't required in this specific example but it's a good practice.
	if m.Author.ID == s.State.User.ID {
		return
	}

	messages[m.Author.ID] = append(messages[m.Author.ID], m.Content)

	if m.Content == "felix password" {

		// get the guild id
		guildID := ext.GuildID(s, m.ChannelID)

		// retrieve the guild struct with the guild id
		guild, _ := s.Guild(guildID)

		// get role id because later we can only get the role by id
		staffID = ext.GuildRoleName(guild, "staff")

		// get member id from the guild list, this makes sure the member is still in the guild
		memID := ext.GetMemberID(guild, m.Author.ID)

		// if the member is in the guild and has the rank we got for staffID send the password
		if ext.IsRole(guild, memID, staffID) == true || memID == guild.OwnerID {
			password := generatePassword()
			users[memID] = loginStruct{ID: memID, nickname: m.Author.Username, password: password, passTime: time.Now().Unix()}
			ext.Dm(memID, password, s)
		}

	}
}

func generatePassword() (password string) {
	var alphabet []string
	var nums = []int{0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
	h := sha256.New()

	for x := 97; x < 123; x++ {
		alphabet = append(alphabet, string(x))
	}
	for l := 0; l < 17; l++ {
		rand.Seed(time.Now().UnixNano())
		password += alphabet[rand.Intn(len(alphabet))]
		time.Sleep(1 * time.Nanosecond)
	}
	for i := 0; i < 5; i++ {
		rand.Seed(time.Now().UnixNano())
		tmp := strconv.Itoa(nums[rand.Intn(len(nums))])
		password += tmp
		time.Sleep(1 * time.Nanosecond)
	}

	h.Write([]byte(password))
	password = fmt.Sprintf("%x", h.Sum(nil))
	alphabet = nil
	nums = nil
	return
}

func checkPasswordTime(s *discordgo.Session) {
	for {
		for _, v := range users {
			if time.Now().Unix()-v.passTime > 60 {
				fmt.Printf("User %s's password is to old\r\n", v.nickname)
				ext.Dm(v.ID, "testing password timer", s)
			}
		}
		time.Sleep(1 * time.Second)
	}
}

func serveIndex(w http.ResponseWriter, r *http.Request){
	http.ServeFile(w,r, "html/index.html")
}

func css(w http.ResponseWriter, r *http.Request){
	http.ServeFile(w,r, "css/style.css")
}

func js(w http.ResponseWriter, r *http.Request){
	http.ServeFile(w,r, "js/script.js")
}

func jsx(w http.ResponseWriter, r *http.Request){
	http.ServeFile(w,r, "jsx/script.jsx")
}
