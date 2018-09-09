package discordgoExtension

import (
	"github.com/bwmarrin/discordgo"
	"log"
)

// returns the guildID that the channel belongs to
func GuildID(s *discordgo.Session,channelID string) (string){
	guild, err := s.Channel(channelID)
	if err != nil{
		log.Fatal(err)
	}
	return guild.ID
}

// send a private message to someone based of their user ID
func Dm(id, message string,s *discordgo.Session){
	privateChanel,_:= s.UserChannelCreate(id)
	_,err := s.ChannelMessageSend(privateChanel.ID, message)
	if err != nil{
		log.Fatal(err)
	}
	privateChanel = nil
}



// returns the id associated with a role name
func GuildRoleName(guild *discordgo.Guild, name string)(r string){
	for _,role := range guild.Roles{
		if role.Name == name {
			r = role.ID
		}
	}
	if r == ""{
		r = "role not found"
	}
	return
}

func GetMemberID(guild *discordgo.Guild, id string)(mID string){
	for _, member := range guild.Members {
		if member.User.ID == id {
			mID = member.User.ID
		}
	}
	return
}

func IsRole(guild *discordgo.Guild,memberID string, role string)(bool){
	for _,mem := range guild.Members {
		if mem.User.ID == memberID {
			for _, roles := range mem.Roles {
				if roles == role {
					return true
				}
			}
		}
	}
	return false
}